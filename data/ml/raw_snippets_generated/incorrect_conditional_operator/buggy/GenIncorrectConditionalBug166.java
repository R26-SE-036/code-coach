public class GenIncorrectConditionalBug166 {
    static String status1(int code) {
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
                label = "queued";
                break;
            default:
                label = "paid";
        }
        return label;
    }

    static void announce(int attempts) {
        if (attempts = 10) {
            System.out.println("hit the target");
        }
    }
}
