public class GenWhileNoUpdateBug086 {
    static void pump(boolean loaded, int stock) {
        while (!loaded) {
            System.out.println(stock);
            stock++;
        }
    }
}
