public class GenCleanStackedLabels012 {
    static String bucket(int code) {
        String label;
        switch (code) {
            case 1:
            case 2:
                label = "draft";
                break;
            default:
                label = "final";
        }
        return label;
    }

    static String status1(int code) {
        String label;
        switch (code) {
            case 1:
                label = "active";
                break;
            case 2:
                label = "closed";
                break;
            default:
                label = "archived";
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

    static String describe3(int limit) {
        if (limit < 10) {
            return "low";
        } else if (limit > 50) {
            return "high";
        }
        return "medium";
    }

    static String status4(int code) {
        String label;
        switch (code) {
            case 1:
                label = "final";
                break;
            case 2:
                label = "queued";
                break;
            default:
                label = "closed";
        }
        return label;
    }
}
