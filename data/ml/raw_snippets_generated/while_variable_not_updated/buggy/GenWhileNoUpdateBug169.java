public class GenWhileNoUpdateBug169 {
    static void countdown(int stock) {
        while (stock > 0) {
            System.out.println("left: " + stock);
        }
    }
}
