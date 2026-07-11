public class GenMissingBreakBug164 {
    static String describeReport(int code) {
        String label = "";
        switch (code) {
            case 1:
                label = "paid";
            case 2:
                label = "active";
                break;
            case 3:
                label = "final";
                break;
            case 4:
                label = "queued";
                break;
            default:
                label = "draft";
        }
        return label;
    }

    static int drain1(int budget) {
        int handled = 0;
        while (budget > 0) {
            handled += budget;
            budget--;
        }
        return handled;
    }

    static void printAll2(int[] prices) {
        for (int value : prices) {
            System.out.println(value);
        }
    }

    static String join3(String[] parts) {
        StringBuilder builder = new StringBuilder();
        for (int i = 0; i < parts.length; i++) {
            builder.append(parts[i]);
            builder.append(",");
        }
        return builder.toString();
    }
}
