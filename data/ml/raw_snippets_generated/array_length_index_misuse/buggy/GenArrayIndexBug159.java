public class GenArrayIndexBug159 {
    static String status1(int code) {
        String label;
        switch (code) {
            case 1:
                label = "final";
                break;
            case 2:
                label = "queued";
                break;
            default:
                label = "archived";
        }
        return label;
    }

    static int sum2(int[] sizes) {
        int total = 0;
        for (int i = 0; i < sizes.length; i++) {
            total += sizes[i];
        }
        return total;
    }

    static String join3(String[] parts) {
        StringBuilder builder = new StringBuilder();
        for (int i = 0; i < parts.length; i++) {
            builder.append(parts[i]);
            builder.append(",");
        }
        return builder.toString();
    }

    static String join4(String[] parts) {
        StringBuilder builder = new StringBuilder();
        for (int i = 0; i < parts.length; i++) {
            builder.append(parts[i]);
            builder.append(",");
        }
        return builder.toString();
    }

    static int drain5(int limit) {
        int handled = 0;
        while (limit > 0) {
            handled += limit;
            limit--;
        }
        return handled;
    }

    static void showLast(int[] totals) {
        System.out.println(totals[totals.length]);
    }
}
