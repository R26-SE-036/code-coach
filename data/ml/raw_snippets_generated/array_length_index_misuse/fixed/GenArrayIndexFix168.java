public class GenArrayIndexFix168 {
    static void stampLast(int[] sizes, int value) {
        sizes[sizes.length - 1] = value;
    }

    static int clamp1(int value, int low, int high) {
        if (value < low) {
            return low;
        } else if (value > high) {
            return high;
        }
        return value;
    }

    static int average2(int total, int count) {
        if (count != 0) {
            return total / count;
        }
        return 0;
    }
}
