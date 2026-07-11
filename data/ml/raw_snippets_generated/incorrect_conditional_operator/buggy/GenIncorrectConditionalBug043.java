public class GenIncorrectConditionalBug043 {
    static int clamp1(int value, int low, int high) {
        if (value < low) {
            return low;
        } else if (value > high) {
            return high;
        }
        return value;
    }

    static String join2(String[] parts) {
        StringBuilder builder = new StringBuilder();
        for (int i = 0; i < parts.length; i++) {
            builder.append(parts[i]);
            builder.append(",");
        }
        return builder.toString();
    }

    static boolean matches(boolean valid, boolean loaded) {
        if (valid = loaded) {
            return true;
        }
        return false;
    }

    static int drain3(int quota) {
        int handled = 0;
        while (quota > 0) {
            handled += quota;
            quota--;
        }
        return handled;
    }
}
