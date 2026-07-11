public class GenMissingBreakFix147 {
    static String describeTicket(int code) {
        String label = "";
        switch (code) {
            case 1:
                label = "final";
                break;
            case 2:
                label = "expired";
                break;
            case 3:
                label = "closed";
                break;
            case 4:
                label = "new";
                break;
            default:
                label = "archived";
        }
        return label;
    }

    static int drain1(int total) {
        int handled = 0;
        while (total > 0) {
            handled += total;
            total--;
        }
        return handled;
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
