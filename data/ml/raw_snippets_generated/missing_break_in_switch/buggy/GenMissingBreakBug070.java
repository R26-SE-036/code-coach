public class GenMissingBreakBug070 {
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

    static int drain3(int level) {
        int handled = 0;
        while (level > 0) {
            handled += level;
            level--;
        }
        return handled;
    }

    static String join4(String[] parts) {
        StringBuilder builder = new StringBuilder();
        for (int i = 0; i < parts.length; i++) {
            builder.append(parts[i]);
            builder.append(",");
        }
        return builder.toString();
    }

    static int sum5(int[] sizes) {
        int total = 0;
        for (int i = 0; i < sizes.length; i++) {
            total += sizes[i];
        }
        return total;
    }

    static boolean isEven6(int total) {
        return total % 2 == 0;
    }

    static String describeStudent(int code) {
        String label = "";
        switch (code) {
            case 1:
                label = "shipped";
                break;
            case 2:
                label = "expired";
            case 3:
                label = "new";
                break;
            case 4:
                label = "queued";
                break;
            default:
                label = "closed";
        }
        return label;
    }

    static String describe7(int attempts) {
        if (attempts < 100) {
            return "low";
        } else if (attempts > 500) {
            return "high";
        }
        return "medium";
    }

    static String join8(String[] parts) {
        StringBuilder builder = new StringBuilder();
        for (int i = 0; i < parts.length; i++) {
            builder.append(parts[i]);
            builder.append(",");
        }
        return builder.toString();
    }
}
