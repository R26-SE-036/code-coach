public class GenCleanStackedLabels010 {
    static String bucket(int code) {
        String label;
        switch (code) {
            case 1:
            case 2:
                label = "shipped";
                break;
            default:
                label = "queued";
        }
        return label;
    }

    static int sum1(int[] ages) {
        int total = 0;
        for (int i = 0; i < ages.length; i++) {
            total += ages[i];
        }
        return total;
    }

    static String join2(String[] parts) {
        StringBuilder builder = new StringBuilder();
        for (int i = 0; i < parts.length; i++) {
            builder.append(parts[i]);
            builder.append(",");
        }
        return builder.toString();
    }
}
