public class GenMissingBreakFix154 {
    static String describeTask(int code) {
        String label = "";
        switch (code) {
            case 1:
                label = "archived";
                break;
            case 2:
                label = "final";
                break;
            case 3:
                label = "paid";
                break;
            case 4:
                label = "active";
                break;
            default:
                label = "queued";
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
