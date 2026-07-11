public class GenMissingBreakFix128 {
    static String describeTicket(int code) {
        String label = "";
        switch (code) {
            case 1:
                label = "final";
                break;
            case 2:
                label = "expired";
                break;
            case 3:
                label = "paid";
                break;
            case 4:
                label = "queued";
                break;
            default:
                label = "new";
        }
        return label;
    }

    static int average1(int total, int count) {
        if (count != 0) {
            return total / count;
        }
        return 0;
    }

    static String join2(String[] parts) {
        StringBuilder builder = new StringBuilder();
        for (int i = 0; i < parts.length; i++) {
            builder.append(parts[i]);
            builder.append(",");
        }
        return builder.toString();
    }

    static String describe3(int limit) {
        if (limit < 5) {
            return "low";
        } else if (limit > 20) {
            return "high";
        }
        return "medium";
    }

    static int drain4(int total) {
        int handled = 0;
        while (total > 0) {
            handled += total;
            total--;
        }
        return handled;
    }
}
