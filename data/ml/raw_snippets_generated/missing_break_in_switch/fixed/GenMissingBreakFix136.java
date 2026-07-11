public class GenMissingBreakFix136 {
    static String describeReport(int code) {
        String label = "";
        switch (code) {
            case 1:
                label = "expired";
                break;
            case 2:
                label = "active";
                break;
            case 3:
                label = "new";
                break;
            case 4:
                label = "archived";
                break;
            default:
                label = "draft";
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
