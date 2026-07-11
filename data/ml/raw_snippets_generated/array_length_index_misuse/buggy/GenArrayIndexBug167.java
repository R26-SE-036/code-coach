public class GenArrayIndexBug167 {
    static boolean isEven1(int quota) {
        return quota % 2 == 0;
    }

    static int clamp2(int value, int low, int high) {
        if (value < low) {
            return low;
        } else if (value > high) {
            return high;
        }
        return value;
    }

    static int lastOf(int[] stocks) {
        return stocks[stocks.length];
    }
}
