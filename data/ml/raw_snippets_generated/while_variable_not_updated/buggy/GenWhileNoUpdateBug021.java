public class GenWhileNoUpdateBug021 {
    static String join1(String[] parts) {
        StringBuilder builder = new StringBuilder();
        for (int i = 0; i < parts.length; i++) {
            builder.append(parts[i]);
            builder.append(",");
        }
        return builder.toString();
    }

    static String describe2(int count) {
        if (count < 5) {
            return "low";
        } else if (count > 20) {
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

    static boolean isEven4(int total) {
        return total % 2 == 0;
    }

    static int gather(int steps, int total) {
        int sum = 0;
        while (steps < total) {
            sum += steps;
        }
        return sum;
    }
}
