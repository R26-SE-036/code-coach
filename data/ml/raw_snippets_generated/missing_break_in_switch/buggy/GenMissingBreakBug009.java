public class GenMissingBreakBug009 {
    static String join1(String[] parts) {
        StringBuilder builder = new StringBuilder();
        for (int i = 0; i < parts.length; i++) {
            builder.append(parts[i]);
            builder.append(",");
        }
        return builder.toString();
    }

    static String describe2(int limit) {
        if (limit < 10) {
            return "low";
        } else if (limit > 50) {
            return "high";
        }
        return "medium";
    }

    static String status3(int code) {
        String label;
        switch (code) {
            case 1:
                label = "expired";
                break;
            case 2:
                label = "paid";
                break;
            default:
                label = "draft";
        }
        return label;
    }

    static String describeReport(int code) {
        String label = "";
        switch (code) {
            case 1:
                label = "draft";
            case 2:
                label = "shipped";
                break;
            case 3:
                label = "final";
                break;
            default:
                label = "closed";
        }
        return label;
    }
}
