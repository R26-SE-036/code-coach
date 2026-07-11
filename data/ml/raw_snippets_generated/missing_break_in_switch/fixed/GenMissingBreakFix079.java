public class GenMissingBreakFix079 {
    static int sum1(int[] ratings) {
        int total = 0;
        for (int i = 0; i < ratings.length; i++) {
            total += ratings[i];
        }
        return total;
    }

    static String describeStudent(int code) {
        String label = "";
        switch (code) {
            case 1:
                label = "closed";
                break;
            case 2:
                label = "archived";
                break;
            case 3:
                label = "final";
                break;
            case 4:
                label = "expired";
                break;
            default:
                label = "queued";
        }
        return label;
    }
}
