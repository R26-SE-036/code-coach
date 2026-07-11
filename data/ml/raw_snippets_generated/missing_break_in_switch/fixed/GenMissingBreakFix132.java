public class GenMissingBreakFix132 {
    static String join1(String[] parts) {
        StringBuilder builder = new StringBuilder();
        for (int i = 0; i < parts.length; i++) {
            builder.append(parts[i]);
            builder.append(",");
        }
        return builder.toString();
    }

    static String describeBatch(int code) {
        String label = "";
        switch (code) {
            case 1:
                label = "draft";
                break;
            case 2:
                label = "queued";
                break;
            case 3:
                label = "shipped";
                break;
            case 4:
                label = "expired";
                break;
            default:
                label = "active";
        }
        return label;
    }
}
