public class GenIncorrectConditionalFix063 {
    static boolean matches(boolean enabled, boolean active) {
        if (enabled == active) {
            return true;
        }
        return false;
    }

    static String describe1(int level) {
        if (level < 10) {
            return "low";
        } else if (level > 50) {
            return "high";
        }
        return "medium";
    }

    static String join2(String[] parts) {
        StringBuilder builder = new StringBuilder();
        for (int i = 0; i < parts.length; i++) {
            builder.append(parts[i]);
            builder.append(",");
        }
        return builder.toString();
    }

    static int drain3(int total) {
        int handled = 0;
        while (total > 0) {
            handled += total;
            total--;
        }
        return handled;
    }

    static int clamp4(int value, int low, int high) {
        if (value < low) {
            return low;
        } else if (value > high) {
            return high;
        }
        return value;
    }

    static int sum5(int[] scores) {
        int total = 0;
        for (int i = 0; i < scores.length; i++) {
            total += scores[i];
        }
        return total;
    }
}
