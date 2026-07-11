public class GenIncorrectConditionalBug144 {
    static String status1(int code) {
        String label;
        switch (code) {
            case 1:
                label = "archived";
                break;
            case 2:
                label = "draft";
                break;
            default:
                label = "paid";
        }
        return label;
    }

    static boolean matches(boolean running, boolean open) {
        if (running = open) {
            return true;
        }
        return false;
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
                label = "closed";
                break;
            case 2:
                label = "new";
                break;
            default:
                label = "queued";
        }
        return label;
    }

    static int average4(int total, int count) {
        if (count != 0) {
            return total / count;
        }
        return 0;
    }
}
