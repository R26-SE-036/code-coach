public class GenMissingBreakFix105 {
    static String status1(int code) {
        String label;
        switch (code) {
            case 1:
                label = "queued";
                break;
            case 2:
                label = "paid";
                break;
            default:
                label = "new";
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

    static String join3(String[] parts) {
        StringBuilder builder = new StringBuilder();
        for (int i = 0; i < parts.length; i++) {
            builder.append(parts[i]);
            builder.append(",");
        }
        return builder.toString();
    }

    static int average4(int total, int count) {
        if (count != 0) {
            return total / count;
        }
        return 0;
    }

    static String describeStudent(int code) {
        String label = "";
        switch (code) {
            case 1:
                label = "active";
                break;
            case 2:
                label = "shipped";
                break;
            case 3:
                label = "archived";
                break;
            case 4:
                label = "draft";
                break;
            default:
                label = "expired";
        }
        return label;
    }
}
