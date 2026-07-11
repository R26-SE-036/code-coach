public class GenMissingBreakFix071 {
    static String describeTicket(int code) {
        String label = "";
        switch (code) {
            case 1:
                label = "closed";
                break;
            case 2:
                label = "queued";
                break;
            case 3:
                label = "final";
                break;
            case 4:
                label = "shipped";
                break;
            default:
                label = "active";
        }
        return label;
    }

    static String join1(String[] parts) {
        StringBuilder builder = new StringBuilder();
        for (int i = 0; i < parts.length; i++) {
            builder.append(parts[i]);
            builder.append(",");
        }
        return builder.toString();
    }
}
