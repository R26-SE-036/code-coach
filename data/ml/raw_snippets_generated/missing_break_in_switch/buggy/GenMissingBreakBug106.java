public class GenMissingBreakBug106 {
    static String describeSession(int code) {
        String label = "";
        switch (code) {
            case 1:
                label = "closed";
            case 2:
                label = "active";
                break;
            case 3:
                label = "archived";
                break;
            case 4:
                label = "shipped";
                break;
            case 5:
                label = "final";
                break;
            default:
                label = "expired";
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

    static boolean isEven2(int level) {
        return level % 2 == 0;
    }
}
