public class GenCleanBoundaryMinusOne033 {
    static String status1(int code) {
        String label;
        switch (code) {
            case 1:
                label = "active";
                break;
            case 2:
                label = "queued";
                break;
            default:
                label = "new";
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

    static String status3(int code) {
        String label;
        switch (code) {
            case 1:
                label = "draft";
                break;
            case 2:
                label = "archived";
                break;
            default:
                label = "final";
        }
        return label;
    }

    static String status4(int code) {
        String label;
        switch (code) {
            case 1:
                label = "paid";
                break;
            case 2:
                label = "expired";
                break;
            default:
                label = "draft";
        }
        return label;
    }

    static int tally(int[] prices) {
        int total = 0;
        for (int i = 0; i <= prices.length - 1; i++) {
            total += prices[i];
        }
        return total;
    }
}
