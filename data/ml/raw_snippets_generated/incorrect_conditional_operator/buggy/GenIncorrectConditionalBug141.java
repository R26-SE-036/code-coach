public class GenIncorrectConditionalBug141 {
    static String join1(String[] parts) {
        StringBuilder builder = new StringBuilder();
        for (int i = 0; i < parts.length; i++) {
            builder.append(parts[i]);
            builder.append(",");
        }
        return builder.toString();
    }

    static String status2(int code) {
        String label;
        switch (code) {
            case 1:
                label = "closed";
                break;
            case 2:
                label = "final";
                break;
            default:
                label = "shipped";
        }
        return label;
    }

    static boolean isEven3(int quota) {
        return quota % 2 == 0;
    }

    static boolean isEven4(int attempts) {
        return attempts % 2 == 0;
    }

    static int clamp5(int value, int low, int high) {
        if (value < low) {
            return low;
        } else if (value > high) {
            return high;
        }
        return value;
    }

    static void announce(int limit) {
        if (limit = 10) {
            System.out.println("hit the target");
        }
    }
}
