public class GenMissingBreakFix041 {
    static String join1(String[] parts) {
        StringBuilder builder = new StringBuilder();
        for (int i = 0; i < parts.length; i++) {
            builder.append(parts[i]);
            builder.append(",");
        }
        return builder.toString();
    }

    static int sum2(int[] ages) {
        int total = 0;
        for (int i = 0; i < ages.length; i++) {
            total += ages[i];
        }
        return total;
    }

    static String describeStudent(int code) {
        String label = "";
        switch (code) {
            case 1:
                label = "draft";
                break;
            case 2:
                label = "closed";
                break;
            case 3:
                label = "final";
                break;
            default:
                label = "new";
        }
        return label;
    }
}
