public class GenMissingBreakBug078 {
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
                label = "shipped";
                break;
            case 2:
                label = "new";
            case 3:
                label = "queued";
                break;
            default:
                label = "expired";
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
}
