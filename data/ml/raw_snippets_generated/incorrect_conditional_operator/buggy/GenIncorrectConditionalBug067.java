public class GenIncorrectConditionalBug067 {
    static String status1(int code) {
        String label;
        switch (code) {
            case 1:
                label = "active";
                break;
            case 2:
                label = "shipped";
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

    static void announce(int count) {
        if (count = 10) {
            System.out.println("hit the target");
        }
    }
}
