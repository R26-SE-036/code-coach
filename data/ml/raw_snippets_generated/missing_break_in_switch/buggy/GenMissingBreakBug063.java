public class GenMissingBreakBug063 {
    static int sum1(int[] scores) {
        int total = 0;
        for (int i = 0; i < scores.length; i++) {
            total += scores[i];
        }
        return total;
    }

    static String describeStudent(int code) {
        String label = "";
        switch (code) {
            case 1:
                label = "expired";
            case 2:
                label = "active";
                break;
            case 3:
                label = "shipped";
                break;
            default:
                label = "final";
        }
        return label;
    }
}
