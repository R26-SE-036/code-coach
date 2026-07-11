public class GenCleanBoundaryMinusOne032 {
    static boolean isEven1(int count) {
        return count % 2 == 0;
    }

    static int tally(int[] marks) {
        int total = 0;
        for (int i = 0; i <= marks.length - 1; i++) {
            total += marks[i];
        }
        return total;
    }

    static int sum2(int[] marks) {
        int total = 0;
        for (int i = 0; i < marks.length; i++) {
            total += marks[i];
        }
        return total;
    }

    static String join3(String[] parts) {
        StringBuilder builder = new StringBuilder();
        for (int i = 0; i < parts.length; i++) {
            builder.append(parts[i]);
            builder.append(",");
        }
        return builder.toString();
    }

    static int clamp4(int value, int low, int high) {
        if (value < low) {
            return low;
        } else if (value > high) {
            return high;
        }
        return value;
    }

    static int clamp5(int value, int low, int high) {
        if (value < low) {
            return low;
        } else if (value > high) {
            return high;
        }
        return value;
    }
}
