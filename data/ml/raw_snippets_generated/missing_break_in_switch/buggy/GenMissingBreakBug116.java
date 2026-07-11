public class GenMissingBreakBug116 {
    static int sum1(int[] weights) {
        int total = 0;
        for (int i = 0; i < weights.length; i++) {
            total += weights[i];
        }
        return total;
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

    static String describe4(int budget) {
        if (budget < 10) {
            return "low";
        } else if (budget > 50) {
            return "high";
        }
        return "medium";
    }

    static String describeReport(int code) {
        String label = "";
        switch (code) {
            case 1:
                label = "paid";
                break;
            case 2:
                label = "shipped";
            case 3:
                label = "closed";
                break;
            case 4:
                label = "queued";
                break;
            case 5:
                label = "final";
                break;
            default:
                label = "archived";
        }
        return label;
    }

    static String describe5(int steps) {
        if (steps < 5) {
            return "low";
        } else if (steps > 20) {
            return "high";
        }
        return "medium";
    }
}
