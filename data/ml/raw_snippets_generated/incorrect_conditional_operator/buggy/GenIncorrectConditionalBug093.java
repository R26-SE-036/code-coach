public class GenIncorrectConditionalBug093 {
    static String join1(String[] parts) {
        StringBuilder builder = new StringBuilder();
        for (int i = 0; i < parts.length; i++) {
            builder.append(parts[i]);
            builder.append(",");
        }
        return builder.toString();
    }

    static String describe2(int total) {
        if (total < 10) {
            return "low";
        } else if (total > 50) {
            return "high";
        }
        return "medium";
    }

    static boolean matches(boolean armed, boolean verified) {
        if (armed = verified) {
            return true;
        }
        return false;
    }

    static String describe3(int total) {
        if (total < 5) {
            return "low";
        } else if (total > 20) {
            return "high";
        }
        return "medium";
    }

    static String describe4(int budget) {
        if (budget < 10) {
            return "low";
        } else if (budget > 50) {
            return "high";
        }
        return "medium";
    }

    static String status5(int code) {
        String label;
        switch (code) {
            case 1:
                label = "queued";
                break;
            case 2:
                label = "paid";
                break;
            default:
                label = "archived";
        }
        return label;
    }
}
