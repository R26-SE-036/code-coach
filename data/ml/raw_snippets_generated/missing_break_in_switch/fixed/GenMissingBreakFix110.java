public class GenMissingBreakFix110 {
    static boolean isEven1(int level) {
        return level % 2 == 0;
    }

    static String join2(String[] parts) {
        StringBuilder builder = new StringBuilder();
        for (int i = 0; i < parts.length; i++) {
            builder.append(parts[i]);
            builder.append(",");
        }
        return builder.toString();
    }

    static boolean isEven3(int budget) {
        return budget % 2 == 0;
    }

    static String describeInvoice(int code) {
        String label = "";
        switch (code) {
            case 1:
                label = "new";
                break;
            case 2:
                label = "active";
                break;
            case 3:
                label = "paid";
                break;
            case 4:
                label = "final";
                break;
            case 5:
                label = "expired";
                break;
            default:
                label = "shipped";
        }
        return label;
    }
}
