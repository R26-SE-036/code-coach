public class GenArrayIndexBug046 {
    static void showLast(int[] ratings) {
        System.out.println(ratings[ratings.length]);
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
