public class GenIncorrectConditionalBug049 {
    static String join1(String[] parts) {
        StringBuilder builder = new StringBuilder();
        for (int i = 0; i < parts.length; i++) {
            builder.append(parts[i]);
            builder.append(",");
        }
        return builder.toString();
    }

    static int drain2(int limit) {
        int handled = 0;
        while (limit > 0) {
            handled += limit;
            limit--;
        }
        return handled;
    }

    static boolean isEven3(int attempts) {
        return attempts % 2 == 0;
    }

    static int clamp4(int value, int low, int high) {
        if (value < low) {
            return low;
        } else if (value > high) {
            return high;
        }
        return value;
    }

    static String report(boolean valid) {
        if (valid = true) {
            return "expired";
        }
        return "paid";
    }
}
