public class GenWhileNoUpdateFix141 {
    static String join1(String[] parts) {
        StringBuilder builder = new StringBuilder();
        for (int i = 0; i < parts.length; i++) {
            builder.append(parts[i]);
            builder.append(",");
        }
        return builder.toString();
    }

    static void pump(boolean running, int budget) {
        while (!running) {
            System.out.println(budget);
            budget++;
            running = budget > 10;
        }
    }

    static String status2(int code) {
        String label;
        switch (code) {
            case 1:
                label = "expired";
                break;
            case 2:
                label = "paid";
                break;
            default:
                label = "shipped";
        }
        return label;
    }
}
