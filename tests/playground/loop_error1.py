def count_100(index):
    idx = index
    for j in range(100):
        idx = idx + 1
    return idx

result = count_100(0)

"""
Wrong generation:

export var count_100 = function (index) {
	var idx = index;
	for (var j = 0; j < 100; j++) {
		var idx = idx + 1;   // var is wrong
	}
	return idx;
};
export var result = count_100 (0);
"""