from typing import List
from itertools import product
import statistics

# ======================================================================================================================
# Do not touch the client message class!
# ======================================================================================================================


class ClientMessage:
	"""
	This class will be filled out and passed to student_entrypoint for your algorithm.
	"""
	total_seconds_elapsed: float	  # The number of simulated seconds elapsed in this test
	previous_throughput: float		  # The measured throughput for the previous chunk in kB/s

	buffer_current_fill: float			# The number of kB currently in the client buffer
	buffer_seconds_per_chunk: float	 # Number of seconds that it takes the client to watch a chunk. Every
										# buffer_seconds_per_chunk, a chunk is consumed from the client buffer.
	buffer_seconds_until_empty: float   # The number of seconds of video left in the client buffer. A chunk must
										# be finished downloading before this time to avoid a rebuffer event.
	buffer_max_size: float			  # The maximum size of the client buffer. If the client buffer is filled beyond
										# maximum, then download will be throttled until the buffer is no longer full

	# The quality bitrates are formatted as follows:
	#
	#   quality_levels is an integer reflecting the # of quality levels you may choose from.
	#
	#   quality_bitrates is a list of floats specifying the number of kilobytes the upcoming chunk is at each quality
	#   level. Quality level 2 always costs twice as much as quality level 1, quality level 3 is twice as big as 2, and
	#   so on.
	#	   quality_bitrates[0] = kB cost for quality level 1
	#	   quality_bitrates[1] = kB cost for quality level 2
	#	   ...
	#
	#   upcoming_quality_bitrates is a list of quality_bitrates for future chunks. Each entry is a list of
	#   quality_bitrates that will be used for an upcoming chunk. Use this for algorithms that look forward multiple
	#   chunks in the future. Will shrink and eventually become empty as streaming approaches the end of the video.
	#	   upcoming_quality_bitrates[0]: Will be used for quality_bitrates in the next student_entrypoint call
	#	   upcoming_quality_bitrates[1]: Will be used for quality_bitrates in the student_entrypoint call after that
	#	   ...
	#
	quality_levels: int
	quality_bitrates: List[float]
	upcoming_quality_bitrates: List[List[float]]

	# You may use these to tune your algorithm to each user case! Remember, you can and should change these in the
	# config files to simulate different clients!
	#
	#   User Quality of Experience =	(Average chunk quality) * (Quality Coefficient) +
	#								   -(Number of changes in chunk quality) * (Variation Coefficient)
	#								   -(Amount of time spent rebuffering) * (Rebuffering Coefficient)
	#
	#   *QoE is then divided by total number of chunks
	#
	quality_coefficient: float
	variation_coefficient: float
	rebuffering_coefficient: float
# ======================================================================================================================


# Your helper functions, variables, classes here. You may also write initialization routines to be called
# when this script is first imported and anything else you wish.

LOOKAHEAD = 5
RESERVOIR = 4.0
CUSHION = 10.0
THROUGHPUT_HISTORY = []
REBUFFER_FLAG = False

def update_bandwidth_history(current):
    global THROUGHPUT_HISTORY
    if current > 0:
        THROUGHPUT_HISTORY.append(current)
    if len(THROUGHPUT_HISTORY) > 10:
        THROUGHPUT_HISTORY = THROUGHPUT_HISTORY[-10:]

def get_bandwidth_stats():
    short = THROUGHPUT_HISTORY[-2:] if len(THROUGHPUT_HISTORY) >= 2 else THROUGHPUT_HISTORY
    long = THROUGHPUT_HISTORY[-5:] if len(THROUGHPUT_HISTORY) >= 5 else THROUGHPUT_HISTORY

    short_avg = statistics.mean(short) if short else 1000.0
    long_avg = statistics.mean(long) if long else 1000.0
    volatility = abs(short_avg - long_avg) / max(short_avg, long_avg)

    return long_avg, volatility

def chuck_weight(chunk_bitrates):
    return [1.0 / (bitrate / (i + 1)) for i, bitrate in enumerate(chunk_bitrates)]

def compute_qoe_sequence(qualities, bitrates, buffer_init, bandwidth, spc, q_coef, v_coef, r_coef, weight, confidence_penalty):
    global REBUFFER_FLAG
    qoe = 0.0
    buffer = buffer_init
    rebuffer = 0.0
    prev_q = None

    for i, q in enumerate(qualities):
        size_kB = bitrates[i][q]
        download_time = size_kB / bandwidth

        if buffer < download_time:
            rebuffer += download_time - buffer
            buffer = 0.0
        else:
            buffer -= download_time

        buffer += spc
        qoe += q * q_coef + weight[i][q] * 0.5

        if prev_q is not None:
            variation_penalty = abs(q - prev_q) * v_coef
            if buffer < CUSHION:
                variation_penalty *= 1.2
            variation_penalty *= (1 + confidence_penalty)
            qoe -= variation_penalty
        prev_q = q

    qoe -= rebuffer * r_coef * (1 + confidence_penalty * 2)
    REBUFFER_FLAG = rebuffer > 0.01  # penalty for rebuffering
    return qoe

def student_entrypoint(client_message: ClientMessage):
	"""
	Your mission, if you choose to accept it, is to build an algorithm for chunk bitrate selection that provides
	the best possible experience for users streaming from your service.

	Construct an algorithm below that selects a quality for a new chunk given the parameters in ClientMessage. Feel
	free to create any helper function, variables, or classes as you wish.

	Simulation does ~NOT~ run in real time. The code you write can be as slow and complicated as you wish without
	penalizing your results. Focus on picking good qualities!

	Also remember the config files are built for one particular client. You can (and should!) adjust the QoE metrics to
	see how it impacts the final user score. How do algorithms work with a client that really hates rebuffering? What
	about when the client doesn't care about variation? For what QoE coefficients does your algorithm work best, and
	for what coefficients does it fail?

	Args:
		client_message : ClientMessage holding the parameters for this chunk and current client state.

	:return: float Your quality choice. Must be one in the range [0 ... quality_levels - 1] inclusive.
	"""

	update_bandwidth_history(client_message.previous_throughput)
	bandwidth_est, confidence_penalty = get_bandwidth_stats()

	buffer_sec = client_message.buffer_seconds_until_empty
	spc = client_message.buffer_seconds_per_chunk
	levels = client_message.quality_levels
     
	if buffer_sec < CUSHION or REBUFFER_FLAG or confidence_penalty > 0.2:
		bandwidth_est *= 0.8

	future_bitrates = [client_message.quality_bitrates] + client_message.upcoming_quality_bitrates
	lookahead_chunks = future_bitrates[:LOOKAHEAD]
	weight = [chuck_weight(c) for c in lookahead_chunks]

	# Conservative fallback
	if buffer_sec <= RESERVOIR:
		return 0
	elif buffer_sec < RESERVOIR + CUSHION:
		f = (buffer_sec - RESERVOIR) / CUSHION
		return int(f * (levels - 1))

	# Lookahead sequence simulation with confidence-aware scoring
	max_qoe = float('-inf')
	max_qoe_seq = [0]

	for seq in product(range(levels), repeat=len(lookahead_chunks)):
		qoe = compute_qoe_sequence(
			qualities=seq,
			bitrates=lookahead_chunks,
			buffer_init=buffer_sec,
			bandwidth=bandwidth_est,
			spc=spc,
			q_coef=client_message.quality_coefficient,
			v_coef=client_message.variation_coefficient,
			r_coef=client_message.rebuffering_coefficient,
			weight=weight,
			confidence_penalty=confidence_penalty
		)
	if qoe > max_qoe:
		max_qoe = qoe
		max_qoe_seq = seq

	return max_qoe_seq[0]