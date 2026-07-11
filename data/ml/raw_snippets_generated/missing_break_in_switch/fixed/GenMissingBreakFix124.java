public class GenMissingBreakFix124 {
    static String status1(int code) {
        String label;
        switch (code) {
            case 1:
                label = "archived";
                break;
            case 2:
                label = "final";
                break;
            default:
                label = "queued";
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

    static String describeTicket(int code) {
        String label = "";
        switch (code) {
            case 1:
                label = "shipped";
                break;
            case 2:
                label = "expired";
                break;
            case 3:
                label = "queued";
                break;
            case 4:
                label = "paid";
                break;
            case 5:
                label = "archived";
                break;
            default:
                label = "final";
        }
        return label;
    }
}
