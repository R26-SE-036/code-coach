public class GenCleanBoundaryMinusOne012 {
    static int clamp1(int value, int low, int high) {
        if (value < low) {
            return low;
        } else if (value > high) {
            return high;
        }
        return value;
    }

    static String describe2(int attempts) {
        if (attempts < 100) {
            return "low";
        } else if (attempts > 500) {
            return "high";
        }
        return "medium";
    }

    static int tally(int[] sizes) {
        int total = 0;
        for (int i = 0; i <= sizes.length - 1; i++) {
            total += sizes[i];
        }
        return total;
    }
}
