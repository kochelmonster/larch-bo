def count_100(index):
    for j in range(100):
        index = index + 1
    return index

result = count_100(0)

"""
Wrong generation:

export var count_100 = function (index) {
	for (var j = 0; j < 100; j++) {
		var index = index + 1;  // var is wrong
	}
	return index;
};
export var result = count_100 (0);
"""
