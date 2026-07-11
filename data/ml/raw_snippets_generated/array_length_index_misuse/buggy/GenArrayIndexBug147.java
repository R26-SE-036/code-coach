public class GenArrayIndexBug147 {
    static void showLast(int[] scores) {
        System.out.println(scores[scores.length]);
    }

    static String status1(int code) {
        String label;
        switch (code) {
            case 1:
                label = "queued";
                break;
            case 2:
                label = "paid";
                break;
            default:
                label = "closed";
        }
        return label;
    }
}
