public class GenArrayIndexBug014 {
    static void printAll1(int[] values) {
        for (int value : values) {
            System.out.println(value);
        }
    }

    static int lastOf(int[] weights) {
        return weights[weights.length];
    }

    static String describe2(int attempts) {
        if (attempts < 10) {
            return "low";
        } else if (attempts > 50) {
            return "high";
        }
        return "medium";
    }

    static int clamp3(int value, int low, int high) {
        if (value < low) {
            return low;
        } else if (value > high) {
            return high;
        }
        return value;
    }
}
