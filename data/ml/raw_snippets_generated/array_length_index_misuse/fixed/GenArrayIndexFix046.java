public class GenArrayIndexFix046 {
    static void showLast(int[] ratings) {
        System.out.println(ratings[ratings.length - 1]);
    }

    static String status1(int code) {
        String label;
        switch (code) {
            case 1:
                label = "shipped";
                break;
            case 2:
                label = "new";
                break;
            default:
                label = "closed";
        }
        return label;
    }
}
