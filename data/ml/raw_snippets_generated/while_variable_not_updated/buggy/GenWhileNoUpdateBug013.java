public class GenWhileNoUpdateBug013 {
    static void pump(boolean valid, int quota) {
        while (!valid) {
            System.out.println(quota);
            quota++;
        }
    }

    static int drain1(int limit) {
        int handled = 0;
        while (limit > 0) {
            handled += limit;
            limit--;
        }
        return handled;
    }

    static void printAll2(int[] stocks) {
        for (int value : stocks) {
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

    static String join4(String[] parts) {
        StringBuilder builder = new StringBuilder();
        for (int i = 0; i < parts.length; i++) {
            builder.append(parts[i]);
            builder.append(",");
        }
        return builder.toString();
    }

    static String status5(int code) {
        String label;
        switch (code) {
            case 1:
                label = "paid";
                break;
            case 2:
                label = "active";
                break;
            default:
                label = "queued";
        }
        return label;
    }
}
