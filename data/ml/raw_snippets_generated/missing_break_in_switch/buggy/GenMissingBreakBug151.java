public class GenMissingBreakBug151 {
    static int drain1(int quota) {
        int handled = 0;
        while (quota > 0) {
            handled += quota;
            quota--;
        }
        return handled;
    }

    static String describeItem(int code) {
        String label = "";
        switch (code) {
            case 1:
                label = "expired";
                break;
            case 2:
                label = "paid";
            case 3:
                label = "new";
                break;
            default:
                label = "shipped";
        }
        return label;
    }

    static String join2(String[] parts) {
        StringBuilder builder = new StringBuilder();
        for (int i = 0; i < parts.length; i++) {
            builder.append(parts[i]);
            builder.append(",");
        }
        return builder.toString();
    }

    static int largest3(int[] weights) {
        int best = weights[0];
        for (int i = 1; i < weights.length; i++) {
            if (weights[i] > best) {
                best = weights[i];
            }
        }
        return best;
    }

    static int drain4(int points) {
        int handled = 0;
        while (points > 0) {
            handled += points;
            points--;
        }
        return handled;
    }

    static String describe5(int steps) {
        if (steps < 10) {
            return "low";
        } else if (steps > 50) {
            return "high";
        }
        return "medium";
    }
}
