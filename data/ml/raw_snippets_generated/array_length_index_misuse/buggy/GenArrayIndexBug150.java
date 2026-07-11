public class GenArrayIndexBug150 {
    static void stampLast(int[] ratings, int value) {
        ratings[ratings.length] = value;
    }

    static int clamp1(int value, int low, int high) {
        if (value < low) {
            return low;
        } else if (value > high) {
            return high;
        }
        return value;
    }

    static boolean isEven2(int steps) {
        return steps % 2 == 0;
    }
}
