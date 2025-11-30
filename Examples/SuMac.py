import itertools
from itertools import combinations
lowerbound = 1
upperbound = 11


def is_increasing(sequence):
    return all(x < y for x, y in zip(sequence, sequence[1:]))

def is_decreasing(sequence):
    return all(x > y for x, y in zip(sequence, sequence[1:]))

def split_sequence(sequence, index, return_part='both'):
    """
    Splits the sequence into two parts at the specified index.

    Parameters:
    - sequence: The list to be split.
    - index: The index at which to split the list.
    - return_part: Specifies which part to return ('front', 'back', or 'both').

    Returns:
    - A tuple containing the front and back sequences if 'both' is specified.
    - The front sequence if 'front' is specified.
    - The back sequence if 'back' is specified.
    """
    front = sequence[:index]
    back = sequence[index:]
    
    if return_part == 'front':
        return front
    elif return_part == 'back':
        return back
    elif return_part == 'both':
        return front, back
    else:
        raise ValueError("Invalid value for return_part. Use 'front', 'back', or 'both'.")


def permutation_tour(lowerbound, upperbound):
    numbers = range(lowerbound,upperbound)
    permutations = list(itertools.permutations(numbers))


def one_lump_sequence(lowerbound, upperbound):
    numbers = range(lowerbound,upperbound)
    permutations = list(itertools.permutations(numbers))

    one_lump_seq_output = []

    for seq in permutations:
        if seq[0] == upperbound-1 or seq[-1] == upperbound-1:
            # skip all sequences that lump is at either head or tail
            pass
        else:
            # lump in middle!!
            first_half_seq = split_sequence(list(seq),(list(seq)).index(upperbound-1), 'front')
            second_half_seq = split_sequence(list(seq),(list(seq)).index(upperbound-1), 'back')
            if is_increasing(first_half_seq) and is_decreasing(second_half_seq):
                one_lump_seq_output.append(seq)
    return one_lump_seq_output

def snake_check(one_lump_seq):
    good_snake = []
    good_lump_seq = []
    snake_seq_check_all = []
    for seq in one_lump_seq:
        snake_seq = generate_index_value_pairs(seq)
        good_snake_flag, snake_seq_check = is_a_good_snake(snake_seq)
        if good_snake_flag:
            good_snake.append(snake_seq)
            good_lump_seq.append(seq)
            snake_seq_check_all.append(snake_seq_check)
    return good_snake, good_lump_seq, snake_seq_check_all

def is_a_good_snake(snake_seq):
    result_set=[]
    snake_seq_check = []
    snake_seq_check.append(snake_seq[0]) # always start with head. 

    break_flag = False
    result_flag = False
    # skip all seq that the value is in it's position. this will cause a cycle snake.
    for item in snake_seq:
        if item[0] == item[1]:
            return False, []
        
    while True:
        next_index = snake_seq_check[-1][1] # get the 2nd item in the last tuple of current snake seq. this should be the index of next tuple to look for
        for item in snake_seq:
            if item[0] == next_index:
                # we got next Tuple
                if not item in snake_seq_check:
                    snake_seq_check.append(item)
                    continue
                else:
                    # this item is already in snake_seq_check list.
                    # print(f"{item} is already in current list")
                    break_flag = True
        if break_flag:
            break

        if len(snake_seq_check) == len(snake_seq):
            # print(snake_seq_check)
            result_flag = True
            break

    return result_flag, snake_seq_check
    

def generate_index_value_pairs(tpl):
    # Create a list of pairs (index, value) for each tuple
    pairs = [(index + 1, value) for index, value in enumerate(tpl)]
    return pairs

def all_items_are_full_tour_seq(seq_list,start_value):
    # only return true when each seq in current seq_list is a full length tour seq
    result_flag = True
    for item in seq_list:
        if len(item) != start_value:
            result_flag = False
            break
    return result_flag


def generate_tour_sequence(start_value):
    seq_list = []

    # intial the list with all pairs start with start value and any other values less than start value but not equal to
    # start_value - 1 as the question defined.

    for i in range(1, start_value - 1):
        seq_list.append([start_value, i])
    # we have first 2 numbers now.
    # will start the tour.

    # add current seq in to the sorted list.
    # for each sub seq in the list, check all possible output seq with new number added and added into the list
    # and then remove current sub seq from the list.
    # stop when all seq in current list are full length list.

    while(not all_items_are_full_tour_seq(seq_list, start_value)):
        current_seq = seq_list.pop()
        current_pairs = find_number_pairs(current_seq)
        
        for p in current_pairs:
            if not abs(p[0] - p[1]) in current_seq:
                new_list = current_seq.copy()
                new_list.append(abs(p[0] - p[1]))
                if not new_list in seq_list:
                    seq_list.append(new_list)
                # we got a new sequence with one additional element.
        seq_list = sorted(seq_list, key=len, reverse=True)
    # print(seq_list)
    # print(len(seq_list))

    # clean up the bad tour seq
    # the tour has to be ended with start_value - 1.
    good_seq = []
    for seq in seq_list:
        if seq[-1] == start_value - 1:
            good_seq.append(seq)

    # print(good_seq)
    print(len(good_seq))


def generate_all_possible_next_tour(current_seq):
    pass


def find_number_pairs(numbers):
    if len(numbers) < 2:
        print("The list must have more than two elements to form pairs.")
        return []

    # Use combinations to generate all unique pairs
    pairs = list(combinations(numbers, 2))
    return pairs


## generate all good 1 lump snake
for bound in range(5,9):
    print(f"number of element : {bound - 1}")
    one_lump_seq_output = one_lump_sequence(1,bound)
    print(f"Number of good 1 lump sequence : {len(one_lump_seq_output)}")
    good_snake, good_lump_seq, snake_seq_check_all= snake_check(one_lump_seq_output)
    print(f"number of good snake : {len(good_snake)}")
    print("-------------------")
    # for lump_seq, original_snake, rearranged_snake in zip(good_lump_seq, good_snake, snake_seq_check_all):
    #     print(lump_seq)
    #     print(original_snake)
    #     print(rearranged_snake)
    #     print('------------------')

# Example usage:
# numbers = [10, 8, 6]
# pairs = find_number_pairs(numbers)
# print(pairs)

generate_tour_sequence(10)
generate_tour_sequence(11)
generate_tour_sequence(12)
generate_tour_sequence(13)
generate_tour_sequence(14)
