public class GenCleanStackedLabels020 {
    static String bucket(int code) {
        String label;
        switch (code) {
            case 1:
            case 2:
                label = "draft";
                break;
            default:
                label = "new";
        }
        return label;
    }

    static String join1(String[] parts) {
        StringBuilder builder = new StringBuilder();
        for (int i = 0; i < parts.length; i++) {
            builder.append(parts[i]);
            builder.append(",");
        }
        return builder.toString();
    }
}
