public class GenMissingBreakBug168 {
    static String describeTask(int code) {
        String label = "";
        switch (code) {
            case 1:
                label = "shipped";
            case 2:
                label = "new";
                break;
            case 3:
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
