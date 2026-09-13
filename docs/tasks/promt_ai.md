# BỘ TỪ ĐIỂN PROMPT AI TẠO ẢNH & VIDEO

Tài liệu này được chia thành 2 phần chính:
- **PHẦN 1**: Xử lý ảnh tĩnh và tạo video tập trung 100% vào SẢN PHẨM (quần áo).
- **PHẦN 2**: Tạo video người mẫu ảo chuyển động từ ảnh tham chiếu (Virtual Try-on / Model Animation).

---

## PHẦN 1: PROMPT XỬ LÝ SẢN PHẨM & ẢNH TĨNH
*(Sử dụng cho các trường hợp chỉ có sản phẩm, không có người mẫu)*

### 1. Tách nền sản phẩm
> **Prompt:** Tách riêng sản phẩm trong ảnh ra nền xanh (không kèm cả người). Giữ nguyên sản phẩm 100%, không thay đổi bất kỳ chi tiết nào. Mép cắt sạch, sắc nét, không lem, không mất chi tiết. Sản phẩm ở giữa khung hình, rõ nét, chất lượng cao. Làm nét ảnh chất lượng 4k. 
> 
> *The product is the absolute priority. Do not redesign, reinterpret or add any details that are not visible in the reference image.*

### 2. Tạo ảnh quảng cáo sản phẩm
> **Prompt:** Gộp sản phẩm với background để tạo thành một ảnh kiểu như chiếc áo được treo lên để giới thiệu sản phẩm đẹp, cân đối, chân thật. Giữ nguyên sản phẩm 100%, không thay đổi bất kỳ chi tiết nào. Nền tối nhẹ để sản phẩm nổi bật hơn. Thêm rất ít phụ kiện nhỏ, đẹp và phù hợp để ảnh đỡ trống, nhưng sản phẩm vẫn là trọng tâm tuyệt đối. Ánh sáng mềm, đẹp, phong cách thương mại, không có người, không text, không logo, không watermark. 
> 
> *Lưu ý: Đây là quần áo trẻ em nên làm cho sản phẩm kích thước vừa phải với bố cục trong ảnh. The product is the absolute priority. Do not redesign, reinterpret or add any clothing details that are not visible in the reference image.*

### 3. Tạo Prompt Video (Video Sản phẩm tĩnh bay/treo)
> **Prompt:** Dựa vào bức ảnh sản phẩm này, hãy tạo nhiều prompt video bán hàng kiểu review ngắn (nhiều góc độ sản phẩm), kiểu như chiếc áo được treo lên để giới thiệu sản phẩm đẹp, cân đối, chân thật, thật phù hợp TikTok Shop/Facebook Reels. Sản phẩm phải thật chính xác, đúng với ảnh tham chiếu. Không có người mẫu, có tay người, không text màn hình, không logo, không watermark. Lưu ý: đây là quần áo trẻ em. Các góc quay đều là toàn cảnh.
>
> *Yêu cầu đầu ra:* Mỗi video khoảng 8 giây, dọc 9:16, nhiều góc quay đẹp, chuyển động mượt, tập trung vào chi tiết nhìn thấy rõ của sản phẩm. Viết thành Video Prompt hoàn chỉnh để copy dùng ngay. The product is the absolute priority. Do not redesign, reinterpret or add any clothing details that are not visible in the reference image.

### 4. Lấy riêng Background (Xóa sản phẩm)
> **Prompt:** Tôi muốn lấy riêng phần background của bức ảnh này để dùng quảng cáo cho các sản phẩm khác. Hãy xóa sản phẩm chính, giữ lại toàn bộ background, ánh sáng, bố cục và phụ kiện trang trí. Làm background hoàn chỉnh, sạch, tự nhiên, không để lại dấu vết của sản phẩm đã xóa.

---

## 🎨 CÁC CONCEPT THAY NỀN (BACKGROUND STYLES)

- **Thảm Lông Xám (Flatlay):** Thay đổi nền của sản phẩm tôi vừa gửi bằng một tấm thảm lông màu xám thẩm mỹ, sản phẩm được trải ra trên sàn với ánh sáng phản chiếu từ cửa sổ, thêm một tấm gương vuông và quần áo phản chiếu nhẹ trong gương, thêm một chiếc mũ, đôi giày, 1 cây cảnh bonsai và một chiếc máy ảnh nhỏ xung quanh. Giữ nguyên mọi chi tiết của sản phẩm. Góc nhìn trung cận như chụp flatlay chuyên nghiệp, thực tế.
- **Ghế Sofa:** Sản phẩm mà tôi gửi nằm trên ghế sofa vải lanh màu be trong một căn phòng hiện đại. Xung quanh sản phẩm là kính râm sành điệu, túi tote vải canvas và những cuốn tạp chí thời trang được sắp xếp khéo léo. Ánh sáng tự nhiên từ cửa sổ tạo ra những bóng đổ mềm mại. Phông nền nổi bật với vải dệt kim và sàn gỗ sáng màu. Tỉ lệ dọc 9:16, ultra HD, ánh sáng điện ảnh.
- **Treo Sào Giá Gỗ:** Tạo 1 bức ảnh sản phẩm này chuyên nghiệp, nhất quán, rõ nét và thẩm mỹ mà không cần người mẫu. Sản phẩm treo gọn gàng trên giá treo quần áo bằng móc gỗ, trong phòng gồm: Kệ sách trắng 6 tầng, cây rũ bên trái, cây đứng bên phải, giỏ mây tầng dưới cùng, giường trắng, tranh lá treo tường. Tone trung tính, ánh sáng dịu nhẹ buổi sáng. Sản phẩm nằm giữa góc trung cận.
- **Cầm Tay Thực Tế:** Tạo hình ảnh sản phẩm chuyên nghiệp với chiếc móc đồ bằng gỗ trơn, được một người đàn ông đeo đồng hồ và vòng tay nam cầm. Không xuất hiện người trong khung hình, chỉ thấy đôi bàn tay. Sản phẩm thẳng tắp, gọn gàng. Sàn nhà thảm họa tiết gỗ, tường thẩm mỹ, không gian mát mẻ, đèn LED trắng, đồng hồ treo tường và tranh trừu tượng. Dọc 9:16, Ultra HD.
- **Sàn Có Đèn Neon:** Chỉnh sửa hình ảnh này! Sản phẩm được trải gọn gàng trên nền thảm xám, có các phụ kiện: gương lớn khung đen, giá giày thể thao, chậu cây đen trắng và đèn neon trang trí chạy dọc góc chân tường. Tỉ lệ 9:16. Giữ nguyên toàn bộ chi tiết sản phẩm, màu trung tính, có vệt nắng chiếu xuyên qua khe cửa.

---

## PHẦN 2: THƯ VIỆN PROMPT NGƯỜI MẪU CHUYỂN ĐỘNG (IMAGE-TO-VIDEO)
*(Dùng cho các công cụ AI Video (Kling/Minimax/Runway) để tạo chuyển động từ ảnh người mẫu có sẵn)*

### 🚶‍♀️ Nhóm 1: Nhân vật bước đi tự tin về phía trước
1. Tạo video dọc 9:16 từ bức ảnh tham chiếu. Cô gái bước đi tự tin với dáng người thẳng và nụ cười tự nhiên, sang trọng. Camera di chuyển mượt mà từ dưới lên, bắt trọn chi tiết trang phục và gương mặt. Giữ ánh sáng mềm mại, đồng đều, không bị chói.
2. Tạo video 9:16 cô gái bước đi duyên dáng về phía camera. Cô giữ dáng người thẳng và nụ cười tự tin, thân thiện. Camera lia từ bước chân lên gương mặt. Đảm bảo ánh sáng đồng đều, không bị lóa hay nhấp nháy, giữ nguyên màu sắc và chất liệu vải.
3. Tạo video dọc 9:16. Cô gái bước đi thanh lịch với nụ cười tự nhiên, thoải mái. Một tay thả tự nhiên theo bước đi, tay kia thả lỏng. Camera bắt đầu từ đôi chân và di chuyển lên khuôn mặt tự tin. Ánh sáng giữ mềm mại.
4. Tạo video 9:16 cô gái bước đi đầy tự tin. Mái tóc khẽ bay khi cô bước, nụ cười tỏa sáng. Camera di chuyển mượt từ trang phục lên gương mặt. Giữ ánh sáng cân bằng.
5. Tạo video dọc 9:16. Cô gái bước đi tự nhiên với dáng người thẳng, nụ cười tự tin, thanh lịch. Camera di chuyển mượt mà từ dưới lên, bắt trọn từng chi tiết trang phục. Màu sắc trang phục đồng bộ từ đầu đến cuối.
6. Tạo video 9:16 cô gái bước đi thoải mái và tự tin. Cô cười tự nhiên, dáng đi thanh lịch. Camera theo dõi từ bước chân lên khuôn mặt. Ánh sáng mềm mại, không bị lóe sáng.
7. Tạo video 9:16. Cô gái bước đi mượt mà về phía camera với cử chỉ thoải mái và nụ cười tự tin. Camera di chuyển nhẹ nhàng từ dưới lên, làm nổi bật trang phục và khuôn mặt thanh lịch.
8. Tạo video dọc 9:16 cô gái bước đi tự tin về phía trước. Cô cười tự nhiên với phong thái sang trọng, điềm tĩnh. Camera lia từ phần thân dưới lên gương mặt. Ánh sáng giữ ổn định, không méo màu.
9. Tạo video 9:16. Cô gái bước đi uyển chuyển, nụ cười nhẹ nhàng nhưng tự tin. Cử chỉ tự nhiên, thoải mái. Camera di chuyển mượt từ bước chân lên gương mặt.
10. Tạo video dọc 9:16 từ bức ảnh tham chiếu. Cô gái bước đi với nụ cười bình tĩnh, thanh lịch, dáng người thẳng và duyên dáng. Camera di chuyển mượt từ bước chân lên gương mặt.
11. Tạo video 9:16 trong đó cô gái bước vài bước thoải mái, tự tin. Một tay di chuyển tự nhiên theo nhịp bước, tay còn lại thả lỏng. Camera lia từ đôi chân lên gương mặt. Bảo toàn chi tiết vải.
12. Tạo video dọc 9:16 của cô gái bước đi duyên dáng với nụ cười thân thiện, tự nhiên. Chuyển động mượt mà. Camera bắt đầu từ phần thân dưới và di chuyển mượt lên gương mặt. Tránh hiệu ứng sáng bóng.
13. Tạo video 9:16. Cô gái bước đi tự nhiên với sự thanh lịch, nụ cười tự tin. Camera di chuyển đều từ chân lên đầu, làm nổi bật trang phục và biểu cảm.
14. Tạo video dọc 9:16 của cô gái bước đi với phong thái tự tin, duyên dáng. Cô cười tự nhiên, bước đi thoải mái. Camera lướt nhẹ từ phần thân dưới lên gương mặt.

### 💁‍♀️ Nhóm 2: Vuốt tóc nhẹ nhàng
1. Tạo video dọc 9:16. Cô gái mỉm cười tự nhiên, nhẹ nhàng đưa tay vuốt tóc từ trước ra sau. Gió thổi nhẹ làm tóc bay mềm mại. Camera bắt đầu ở phần trên cơ thể và zoom dần vào gương mặt.
2. Tạo video 9:16. Cô gái cười thanh lịch, một tay vuốt tóc qua vai một cách nhẹ nhàng. Gió nhẹ lướt qua làm mái tóc bay tự nhiên. Camera xoay chậm vòng quanh từ góc chéo trái lên phía trước.
3. Tạo video dọc 9:16. Cô gái mỉm cười ấm áp, tay phải khẽ vuốt tóc, mắt nhìn tự tin về phía trước. Gió thổi làm tóc tung bay nhẹ nhàng. Camera di chuyển từ dưới lên đến khi zoom vào gương mặt.
4. Tạo video 9:16. Cô gái vuốt tóc sang một bên trong khi mỉm cười duyên dáng. Gió thổi làm tóc bay nhẹ tự nhiên. Camera lia ngang từ trái sang phải, bắt trọn từng chi tiết chuyển động của bàn tay.
5. Tạo video dọc 9:16. Cô gái vuốt nhẹ tóc từ bên tai xuống, gương mặt cười thân thiện. Gió nhẹ làm tóc bay mềm. Camera zoom chậm vào khuôn mặt và phần tóc đang được vuốt.
6. Tạo video 9:16. Cô gái bước chậm rãi về phía trước, một tay vuốt tóc nhẹ nhàng, cười thoải mái. Gió thổi tự nhiên làm tóc bay. Camera theo dõi chuyển động từ toàn thân đến cận cảnh khuôn mặt.
7. Tạo video dọc 9:16. Cô gái cười tự nhiên, tay khẽ vuốt tóc ra sau vai. Gió làm tóc chuyển động mềm mại. Camera xoay vòng nhẹ 180 độ từ sau ra trước.
8. Tạo video 9:16. Cô gái ngẩng mặt cười tươi, tay vuốt tóc từ trán sang bên. Gió thổi nhẹ làm tóc lay động. Camera di chuyển chậm từ phần ngực lên đến cận cảnh khuôn mặt.
9. Tạo video dọc 9:16. Cô gái cười dịu dàng, một tay vuốt tóc mượt mà. Camera tiến lại gần từ góc chéo dưới, nhấn mạnh chi tiết chất liệu áo và thần thái thân thiện.
10. Tạo video 9:16. Cô gái vuốt tóc nhẹ nhàng và mỉm cười tự tin. Camera lùi chậm từ cận cảnh khuôn mặt ra toàn thân, bắt trọn trang phục và thần thái sang trọng.
11. Tạo video dọc 9:16. Cô gái nhẹ nhàng đưa tay vuốt tóc cùng với nụ cười dịu dàng. Cơn gió nhẹ thổi qua làm mái tóc bay. Camera từ từ zoom từ phần thân trên đến gương mặt.
12. Tạo video dọc 9:16. Cô gái mỉm cười ấm áp khi vuốt tóc một cách duyên dáng. Gió thổi nhẹ, nâng vài lọn tóc bay tự nhiên. Camera nghiêng lên từ góc bên hông.
13. Tạo video dọc 9:16. Cô gái mỉm cười nhẹ nhàng khi đưa tay vuốt tóc từ trước ra sau. Camera di chuyển lại gần từ góc chéo hướng lên.
14. Tạo video dọc 9:16. Với nụ cười tự nhiên và ánh mắt thư thái, cô gái chạm nhẹ vào tóc, để tóc rơi tự nhiên theo gió. Camera bắt đầu với khung cảnh rộng rồi tiến dần về phía gương mặt.
15. Tạo video dọc 9:16. Cô gái mỉm cười thân thiện khi khẽ dùng tay vuốt tóc. Camera tiến lại từ góc chéo thấp, bắt trọn gương mặt rạng rỡ và chi tiết chất liệu trang phục, đảm bảo không bị méo.

### 💃 Nhóm 3: Xoay người 360 độ (Trình diễn Form dáng)
1. Tạo video dọc 9:16. Cô gái mỉm cười tự nhiên, xoay người chậm rãi 360°, dáng điệu thanh lịch. Camera lia theo vòng xoay, bắt trọn từng chi tiết bộ trang phục mà không làm biến dạng hay thay đổi màu sắc.
2. Tạo video dọc 9:16. Cô gái xoay người 360° một cách uyển chuyển, giữ dáng người thẳng và nụ cười dịu dàng. Camera di chuyển đồng bộ theo vòng xoay để nhấn mạnh từng góc độ của trang phục.
3. Tạo video dọc 9:16. Cô gái bước nhẹ vài bước rồi xoay chậm 360°, mái tóc bay nhẹ trong gió. Camera lia mượt từ đầu đến chân, đảm bảo chi tiết trang phục giữ nguyên, không lỗi hay biến dạng.
4. Tạo video dọc 9:16. Cô gái xoay người chậm, một tay thả tự nhiên, một tay vuốt tóc. Camera quay vòng tròn theo, nhấn mạnh vẻ sang trọng và giữ nguyên chi tiết vải.
5. Tạo video dọc 9:16. Cô gái xoay trọn 360° với nụ cười tự tin. Camera bắt đầu từ góc thấp, lia dần lên theo vòng xoay, làm nổi bật toàn bộ thiết kế bộ trang phục.
6. Tạo video dọc 9:16. Cô gái xoay chậm 360°, giữ nhịp độ đều đặn để người xem thấy rõ mọi góc độ trang phục. Camera lia mượt, ánh sáng giữ ổn định, không chói.
7. Tạo video dọc 9:16. Cô gái xoay 360° trong không gian sang trọng, gương mặt tươi tắn. Camera di chuyển quanh cô gái, bắt trọn chi tiết trang phục từ nhiều góc khác nhau.
8. Tạo video dọc 9:16. Cô gái xoay chậm rãi một vòng 360°, dáng đứng thẳng, nụ cười thân thiện. Camera giữ khoảng cách hợp lý, lia theo mượt mà để tránh biến dạng sản phẩm.
9. Tạo video dọc 9:16. Cô gái xoay trọn vòng, tốc độ chậm, kết hợp nụ cười nhẹ nhàng. Camera từ từ zoom vào trang phục khi cô gái xoay, nhấn mạnh sự tinh tế của chất liệu.
10. Tạo video dọc 9:16. Cô gái xoay 360° duyên dáng, mái tóc nhẹ nhàng tung bay. Camera lia theo chuyển động, giữ đúng chi tiết và màu sắc của sản phẩm từ đầu đến cuối.
11. Tạo video dọc 9:16. Cô gái xoay người chậm rãi 360°, ánh mắt nhìn thẳng vào camera với nụ cười thân thiện. Camera lia trọn vòng, đảm bảo trang phục giữ nguyên thiết kế.
12. Tạo video dọc 9:16. Cô gái xoay 360° trong tư thế thoải mái, một tay khẽ đặt bên hông. Camera lia đều theo vòng xoay, giữ ánh sáng tự nhiên và chi tiết sắc nét.