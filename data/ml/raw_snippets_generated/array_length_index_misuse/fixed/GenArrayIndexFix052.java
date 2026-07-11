public class GenArrayIndexFix052 {
    static boolean isEven1(int budget) {
        return budget % 2 == 0;
    }

    static String join2(String[] parts) {
        StringBuilder builder = new StringBuilder();
        for (int i = 0; i < parts.length; i++) {
            builder.append(parts[i]);
            builder.append(",");
        }
        return builder.toString();
    }

    static int clamp3(int value, int low, int high) {
        if (value < low) {
            return low;
        } else if (value > high) {
            return high;
        }
        return value;
    }

    static int average4(int total, int count) {
        if (count != 0) {
            return total / count;
        }
        return 0;
    }

    static int largest5(int[] marks) {
        int best = marks[0];
        for (int i = 1; i < marks.length; i++) {
            if (marks[i] > best) {
                best = marks[i];
            }
        }
        return best;
    }

    static boolean isEven6(int limit) {
        return limit % 2 == 0;
    }

    static boolean isEven7(int quota) {
        return quota % 2 == 0;
    }

    static int lastOf(int[] weights) {
        return weights[weights.length - 1];
    }
}
